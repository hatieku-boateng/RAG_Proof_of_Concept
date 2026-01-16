import { NextResponse } from "next/server";
import { getOpenAIClient } from "@/lib/openai";

type Body = {
    assistantId: string;
    threadId: string;
    message: string;
};

export async function POST(req: Request) {
    try {
        const body = (await req.json()) as Body;

        if (!body.assistantId || !body.threadId || !body.message) {
            return NextResponse.json(
                { error: "assistantId, threadId, and message are required" },
                { status: 400 },
            );
        }

        const client = getOpenAIClient();

        await client.beta.threads.messages.create(body.threadId, {
            role: "user",
            content: body.message,
        });

        let run = await client.beta.threads.runs.create(body.threadId, {
            assistant_id: body.assistantId,
        });

        const startedAt = Date.now();
        const timeoutMs = 60_000;

        while (["queued", "in_progress", "cancelling"].includes(run.status)) {
            if (Date.now() - startedAt > timeoutMs) {
                return NextResponse.json({ error: "Run timed out" }, { status: 504 });
            }
            await new Promise((r) => setTimeout(r, 500));
            run = await client.beta.threads.runs.retrieve(body.threadId, run.id);
        }

        if (run.status !== "completed") {
            return NextResponse.json(
                { error: `Run ended with status ${run.status}` },
                { status: 500 },
            );
        }

        const messages = await client.beta.threads.messages.list(body.threadId);

        for (const m of messages.data) {
            if (m.role !== "assistant") continue;
            for (const c of m.content) {
                if (c.type === "text") {
                    return NextResponse.json({ reply: c.text.value });
                }
            }
        }

        return NextResponse.json({ reply: "" });
    } catch (err) {
        console.error("/api/chat failed", err);
        const message = err instanceof Error ? err.message : "Unknown error";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
