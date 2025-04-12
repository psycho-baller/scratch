import { task } from "@trigger.dev/sdk/v3";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export const openaiTask = task({
  id: "openai-task",
  //specifying retry options overrides the defaults defined in your trigger.config file
  retry: {
    maxAttempts: 10,
    factor: 1.8,
    minTimeoutInMs: 500,
    maxTimeoutInMs: 30_000,
    randomize: false,
  },
  run: async (payload: { prompt: string }) => {
    const prompt = `
Your goal is to take this transcript, which might contain transcription inaccuracies, and correct these transcription-induced errors to the best of your abilities while following these guidelines:
1. Fix common typographical errors, including but not limited to spelling mistakes, misuse of punctuation, incomplete sentences, and improper capitalization.
2. Use context and common sense to correct errors
3. Only fix clear errors, don't alter the content unnecessarily
4. I sometimes say something twice so that I make sure the speech-to-text accurately transcribes what I am trying to say. So just be aware of that fact and emit the things that seem to be repeated after each other
5. Ignore the speaker numbers and timestamps.  For example: 'Speaker 2 03:57' or 'Speaker 1 01:15'
6. Maintain a similar writing style as the way I speak, which is first person, and
7. Group my transcript into different headings, each one tackling a different topic

+++ TRANSCRIPT
${payload.prompt}


+++ CLEANED TRANSCRIPT
`;
    //if this fails, it will throw an error and retry
    const chatCompletion = await openai.chat.completions.create({
      messages: [
        {
          role: "system",
          content:
            "You are a Transcript Refiner GPT. Your task is to refine transcriptions for clarity and accuracy.",
        },
        { role: "user", content: prompt },
      ],
      model: "chatgpt-4o-latest",
    });

    if (chatCompletion.choices[0]?.message.content === undefined) {
      //sometimes OpenAI returns an empty response, let's retry by throwing an error
      throw new Error("OpenAI call failed");
    }

    const cleanedTranscript = chatCompletion.choices[0].message.content;

    console.log("Cleaned transcript:", cleanedTranscript);

    return cleanedTranscript;
  },
});
