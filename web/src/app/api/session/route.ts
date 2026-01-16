import { NextResponse } from "next/server";
import { getAssistantModel, getOpenAIClient } from "@/lib/openai";

type Body = {
    vectorStoreId: string;
    vectorStoreName?: string;
};

export async function POST(req: Request) {
    try {
        const body = (await req.json()) as Body;

        if (!body.vectorStoreId) {
            return NextResponse.json({ error: "vectorStoreId is required" }, { status: 400 });
        }

        const client = getOpenAIClient();
        const model = getAssistantModel();

        const assistant = await client.beta.assistants.create({
            name: `Assistant for ${body.vectorStoreName || body.vectorStoreId}`,
            model,
            instructions:
                `You are a knowledgeable AI assistant with access to documents in the '${body.vectorStoreName || "selected"}' knowledge base.\n\n` +
                `Your role is to:\n` +
                `- Strictly provide accurate, detailed answers based on the documents in the knowledge base only and nothing else.\n` +
                `- Strictly decline to answer any questions that are not related to the documents in the knowledge base.\n` +
                `- Your response should be well crafted and easy to understand.\n\n` +
                `Always prioritize accuracy and cite your sources when answering questions.`,
            tools: [{ type: "file_search" }],
            tool_resources: {
                file_search: {
                    vector_store_ids: [body.vectorStoreId],
                },
            },
        });

        const thread = await client.beta.threads.create();

        return NextResponse.json({
            assistantId: assistant.id,
            threadId: thread.id,
            model,
        });
    } catch (err) {
        const message = err instanceof Error ? err.message : "Unknown error";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
