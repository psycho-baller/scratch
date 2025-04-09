// Import Supabase Edge Runtime type definitions
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import "jsr:@std/dotenv/load";
// Import the Trigger.dev tasks SDK from npm
// import { tasks } from "@trigger.dev/sdk/v3";
import { tasks } from "npm:@trigger.dev/sdk@latest/v3";
// Import the type for your helloWorldTask (make sure the path is correct)
import type { openaiTask } from "../../../trigger/openai.ts";
// Import djwt functions for creating and handling JWTs
import { create, getNumericDate } from "https://deno.land/x/djwt@v2.8/mod.ts";

const GOOGLE_OAUTH_TOKEN = Deno.env.get("GOOGLE_OAUTH_TOKEN");
// Start the Deno server to handle incoming HTTP requests
Deno.serve(async (req) => {
  try {
    // Only allow POST requests.
    if (req.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Extract the resource state header.
    const resourceState = req.headers.get("X-Goog-Resource-State");
    let taskResult: any = null;

    // Proceed if the notification indicates a change or an addition.
    if (resourceState === "change" || resourceState === "add") {
      // Extract the file ID from the header "X-Goog-Resource-Id".
      const fileId = req.headers.get("X-Goog-Resource-Id");
      if (!fileId) {
        console.error("File ID not provided in headers.");
        return new Response("Bad Request: Missing file ID", { status: 400 });
      }

      // Obtain an OAuth token using service account credentials.
      const oauthToken = await getOAuthToken();

      // Fetch file metadata from the Google Drive API.
      const metadataResponse = await fetch(
        `https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,mimeType,name`,
        {
          headers: { Authorization: `Bearer ${oauthToken}` },
        },
      );

      if (!metadataResponse.ok) {
        const errText = await metadataResponse.text();
        throw new Error(`Failed to fetch file metadata: ${errText}`);
      }

      const metadata = await metadataResponse.json();

      // Check if the file is a Google Docs file.
      if (metadata.mimeType === "application/vnd.google-apps.document") {
        console.log("New Google Docs file detected:", metadata.name);
        taskResult = await callTriggerDevTask(metadata);
      } else {
        console.log("File is not a Google Docs file; ignoring.");
      }
    }

    // Return a successful response. You can include result data as needed.
    return new Response(
      JSON.stringify({ status: "success" }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (error) {
    console.error("Error triggering task:", error);
    // Return an error response in case the task invocation fails.
    return new Response(
      JSON.stringify({ status: "error", message: "Task invocation failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});

/**
 * Refreshes the OAuth token using your stored refresh token.
 */
async function getAccessToken(): Promise<string> {
  const refreshToken = Deno.env.get("OAUTH_REFRESH_TOKEN");
  const clientId = Deno.env.get("CLIENT_ID");
  const clientSecret = Deno.env.get("CLIENT_SECRET");
  const redirectUri = Deno.env.get("REDIRECT_URI") || "http://localhost"; // Your redirect URI if needed

  if (!refreshToken || !clientId || !clientSecret) {
    throw new Error("Missing OAuth credentials in environment variables.");
  }

  const params = new URLSearchParams();
  params.append("client_id", clientId);
  params.append("client_secret", clientSecret);
  params.append("refresh_token", refreshToken);
  params.append("grant_type", "refresh_token");

  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to refresh access token: ${errorText}`);
  }

  const tokenData = await response.json();
  return tokenData.access_token;
}

/**
 * Generates an OAuth token using your service account credentials.
 * Assumes the credentials JSON is stored in the SERVICE_ACCOUNT_JSON environment variable.
 */
async function getOAuthToken(): Promise<string> {
  const svcAccountJson = Deno.env.get("SERVICE_ACCOUNT_JSON");
  if (!svcAccountJson) {
    throw new Error("SERVICE_ACCOUNT_JSON environment variable not set.");
  }
  const serviceAccount = JSON.parse(svcAccountJson);
  const privateKey = serviceAccount.private_key;
  const serviceAccountEmail = serviceAccount.client_email;

  // Define the JWT payload and header.
  const payload = {
    iss: serviceAccountEmail,
    scope: "https://www.googleapis.com/auth/drive",
    aud: "https://oauth2.googleapis.com/token",
    iat: getNumericDate(0),
    exp: getNumericDate(3600), // Token valid for 1 hour
  };
  const header = { alg: "RS256", typ: "JWT" };

  const jwt = await create(header, payload, privateKey);

  // Prepare parameters for exchanging the JWT for an access token.
  const params = new URLSearchParams();
  params.append("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer");
  params.append("assertion", jwt);

  const response = await fetch("https://oauth2.googleapis.com/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: params,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to obtain OAuth token: ${errText}`);
  }

  const tokenData = await response.json();
  return tokenData.access_token;
}

async function callTriggerDevTask(fileMetadata) {
  // Trigger the helloWorldTask defined on Trigger.dev.
  // In this call, we pass "hello-world" as the task ID and "hello" as the payload.
  const result = await tasks.trigger<typeof openaiTask>("openai-task", {
    prompt: "hello",
  });

  // Log result if needed
  console.log("Trigger.dev task result:", result);
  // const triggerUrl = "https://api.trigger.dev/your-task-endpoint";
  // const triggerSecret = process.env.TRIGGER_SECRET_KEY;
  // await fetch(triggerUrl, {
  //   method: "POST",
  //   headers: {
  //     "Content-Type": "application/json",
  //     "Authorization": `Bearer ${triggerSecret}`
  //   },
  //   body: JSON.stringify({
  //     message: "New Google Docs file created",
  //     file: fileMetadata
  //   })
  // });
}
