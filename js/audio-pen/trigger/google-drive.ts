import { task } from "@trigger.dev/sdk/v3";
import { } from "@trigger.dev/sdk/v3";

export const googleDocSummarizer = task({
  id: "google-doc-summarizer",

  trigger: googleDrive.onFileChange({ folderId: "your-folder-id" }),
  integrations: { googleDrive, openai, telegram },
  run: async (payload, io) => {
    // Check if file is a Google Doc
    if (payload.mimeType !== "application/vnd.google-apps.document") {
      return;
    }

    // Extract document content
    const content = await io.googleDrive.getFileContent(payload.fileId);

    // Summarize content with OpenAI
    const summary = await io.openai.createChatCompletion({
      model: "gpt-3.5-turbo",
      messages: [{ role: "user", content: `Summarize this: ${content}` }],
    });

    // Send summary via Telegram
    await io.telegram.sendMessage({
      chatId: "your-chat-id",
      text: `Summary:\n${summary}`,
    });
  },
});
