import { NextResponse } from "next/server";
import { getOpenAIClient } from "@/lib/openai";

export async function GET() {
    try {
        const client = getOpenAIClient();
        const anyClient = client as any;
        const stores = await (anyClient.vectorStores?.list
            ? anyClient.vectorStores.list()
            : anyClient.vector_stores?.list
                ? anyClient.vector_stores.list()
                : Promise.reject(
                    new Error(
                        "OpenAI client does not support vector store listing. Check the openai npm package version.",
                    ),
                ));

        const data = stores.data.map((vs: any) => ({
            id: vs.id,
            name: vs.name,
            status: vs.status,
            fileCounts: vs.file_counts,
            createdAt: vs.created_at,
        }));

        return NextResponse.json({ data });
    } catch (err) {
        console.error("/api/vector-stores failed", err);
        const message = err instanceof Error ? err.message : "Unknown error";
        return NextResponse.json({ error: message }, { status: 500 });
    }
}
