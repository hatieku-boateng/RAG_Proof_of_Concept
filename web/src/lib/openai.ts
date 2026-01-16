import OpenAI from "openai";

export function getOpenAIClient() {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
        throw new Error("OPENAI_API_KEY is not set. Add it to web/.env.local");
    }
    return new OpenAI({
        apiKey,
        defaultHeaders: {
            "OpenAI-Beta": "assistants=v2",
        },
    });
}

export function getAssistantModel() {
    return process.env.OPENAI_MODEL || "gpt-4o-mini";
}
