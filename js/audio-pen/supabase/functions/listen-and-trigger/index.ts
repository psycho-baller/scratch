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

// Start the Deno server to handle incoming HTTP requests
// Start a server using Deno.serve that will handle incoming HTTP requests.
Deno.serve(async (req) => {
  try {
    // Check if the incoming request method is POST; if not, return a 405 Method Not Allowed response.
    if (req.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Retrieve the "X-Goog-Resource-State" header which indicates the type of change (e.g. "change" or "add").
    const resourceState = req.headers.get("X-Goog-Resource-State");
    // Initialize a variable to store the result of the task trigger, if applicable.
    let taskResult: any = null;

    // If the resource state is either "change" or "add", proceed to process the notification.
    if (resourceState === "change" || resourceState === "add") {
      // Retrieve the file ID from the "X-Goog-Resource-Id" header.
      const resourceId = req.headers.get("X-Goog-Resource-Id");
      // If the file ID is missing, log an error and return a 400 Bad Request response.
      if (!resourceId) {
        console.error("File ID not provided in headers.");
        return new Response("Bad Request: Missing file ID", { status: 400 });
      }

      // Call a helper function getAccessToken() to obtain an OAuth token via the refresh token flow.
      const oauthToken = await getAccessToken();

      // Option A: Use changes.list to get the mapping
      // Assume you have a function getChanges(startChangeId) that calls:
      // GET https://www.googleapis.com/drive/v3/changes?startChangeId=YOUR_LAST_KNOWN_CHANGE_ID
      const changes = await getChanges(oauthToken);

      // Find the change that corresponds to the resourceId in the changes list:
      // const change = changes.find((c: any) => c.resourceId === resourceId);
      // if (!change || !change.fileId) {
      //   throw new Error("Could not match resource id with a valid file id.");
      // }
      const fileId = changes.at(-1)?.fileId;

      // Use the access token to fetch file metadata from the Google Drive API.
      // The URL requests specific fields: id, mimeType, and name.
      const metadataResponse = await fetch(
        `https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,mimeType,name`,
        {
          // Set the Authorization header with the obtained token.
          headers: { Authorization: `Bearer ${oauthToken}` },
        },
      );

      // If the metadata request was not successful, retrieve the error text and throw an error.
      if (!metadataResponse.ok) {
        const errText = await metadataResponse.text();
        throw new Error(`Failed to fetch file metadata: ${errText}`);
      }

      // Parse the response body as JSON to obtain the file metadata.
      const metadata = await metadataResponse.json();
      // Check if the file's mimeType indicates that it's a Google Docs document.
      if (metadata.mimeType === "application/vnd.google-apps.document") {
        // Log that a new Google Docs file has been detected (logging its name).
        console.log("New Google Docs file detected:", metadata.name);
        // Call a helper function callTriggerDevTask() to trigger your Trigger.dev task with the metadata.
        taskResult = await callTriggerDevTask(metadata);
      } else {
        // If the file is not a Google Docs file, log that it is being ignored.
        console.log("File is not a Google Docs file; ignoring.");
      }
    }

    // Return a JSON response indicating success. In this example, the status is set to "meow".
    return new Response(
      JSON.stringify({ status: "meow" }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (error) {
    // Log any error that occurs during the processing of the request.
    console.error("Error triggering task:", error);
    // Return a 500 Internal Server Error response with a JSON message.
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

  console.log("Fetching access token...", {
    refreshToken,
    clientId,
    clientSecret,
  });
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
 * Retrieve the list of changes from Google Drive starting from the given token.
 *
 * @param {string} savedStartPageToken - The token from which to start listing changes.
 * @param {string} oauthToken - A valid OAuth access token with the "https://www.googleapis.com/auth/drive.readonly" scope.
 * @returns {Promise<string[]>} - Returns a promise that resolves to the new start page token.
 */
async function getChanges(
  oauthToken: string,
  savedStartPageToken: string = "74871",
): Promise<string[]> {
  // Build the URL for the changes.list endpoint.
  // Add the pageToken and fields parameters to the query string.
  const url = new URL("https://www.googleapis.com/drive/v3/changes");
  url.searchParams.append("pageToken", savedStartPageToken);
  // Use "*" to request all fields from the changes response.
  url.searchParams.append("fields", "*");

  // Make the HTTP GET request to the Google Drive API endpoint.
  const response = await fetch(url.toString(), {
    headers: {
      "Authorization": `Bearer ${oauthToken}`, // Include the access token in the Authorization header.
    },
  });

  // If the HTTP response is not OK, throw an error with the response text.
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to fetch changes: ${errText}`);
  }

  // Parse the JSON response from Google Drive.
  const data = await response.json();

  // If there are changes in the response, log each one.
  if (data.changes && Array.isArray(data.changes)) {
    data.changes.forEach((change: any) => {
      console.log("Change found for file:", change.fileId);
    });
  } else {
    console.log("No changes found in this request.");
  }

  // Return the newStartPageToken from the response.
  // This token is needed for the next request to continue listing changes.
  console.log(`${data.newStartPageToken}, ${savedStartPageToken}`);
  return data.changes;
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
