// Import the built-in Supabase Edge Runtime type definitions for Deno
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
// Load environment variables from a local .env file (only works locally)
import "https://deno.land/std/dotenv/load.ts";
// Import the Trigger.dev tasks SDK from npm
import { tasks } from "npm:@trigger.dev/sdk@latest/v3";
// Import the type for your OpenAI task (adjust the path as needed)
import type { openaiTask } from "../../../trigger/openai.ts";
// Import djwt functions for creating and handling JWTs
import { create, getNumericDate } from "https://deno.land/x/djwt@v2.8/mod.ts";

/** Interface for a single change from the Google Drive API */
interface DriveChange {
  fileId: string;
  resourceId: string;
  [key: string]: any;
}

/** Interface for the changes.list response */
interface ChangesResponse {
  changes?: DriveChange[];
  newStartPageToken?: string;
}

/** Interface representing file metadata from Google Drive */
interface DriveMetadata {
  id: string;
  mimeType: string;
  name: string;
  [key: string]: any;
}

/** Interface for the OAuth token response from Google */
interface OAuthTokenResponse {
  access_token: string;
  expires_in: number;
  token_type: string;
  scope?: string;
  refresh_token?: string;
}

/**
 * Main function that serves as the webhook endpoint.
 * It listens for POST requests from Google Drive push notifications.
 */
Deno.serve(async (req: Request): Promise<Response> => {
  try {
    // Only allow POST requests.
    if (req.method !== "POST") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Retrieve the "X-Goog-Resource-State" header to know what kind of change occurred.
    const resourceState: string | null = req.headers.get(
      "X-Goog-Resource-State",
    );

    // Initialize a variable to store the result from calling a Trigger.dev task.
    let taskResult: unknown = null;

    // If resource state indicates a change or a new addition, process the notification.
    if (resourceState === "change" || resourceState === "add") {
      // Retrieve the resource (file) ID from the header.
      const resourceId: string | null = req.headers.get("X-Goog-Resource-Id");
      if (!resourceId) {
        console.error("File ID not provided in headers.");
        return new Response("Bad Request: Missing file ID", { status: 400 });
      }

      // Obtain a fresh OAuth token using the refresh token flow.
      const oauthToken: string = await getAccessToken();

      // Use changes.list to get the mapping from resource id to real file id.
      // (For simplicity, we assume getChanges returns an array of changes.)
      const changes: DriveChange[] = await getChanges(oauthToken);
      // Here we attempt to find a change whose resourceId matches the one we received.
      const matchingChange = changes.find((c: DriveChange) =>
        c.resourceId === resourceId
      );

      if (!matchingChange || !matchingChange.fileId) {
        throw new Error("Could not match resource id with a valid file id.");
      }
      const fileId: string = matchingChange.fileId;

      // Fetch file metadata using the actual fileId from Google Drive.
      const metadataResponse: Response = await fetch(
        `https://www.googleapis.com/drive/v3/files/${fileId}?fields=id,mimeType,name`,
        {
          headers: { Authorization: `Bearer ${oauthToken}` },
        },
      );

      // Throw an error if fetching metadata was unsuccessful.
      if (!metadataResponse.ok) {
        const errText = await metadataResponse.text();
        throw new Error(`Failed to fetch file metadata: ${errText}`);
      }

      // Parse the file metadata JSON.
      const metadata: DriveMetadata = await metadataResponse.json();

      // Check if the file is a Google Docs document.
      if (metadata.mimeType === "application/vnd.google-apps.document") {
        console.log("New Google Docs file detected:", metadata.name);
        // Fetch the content of the Google Docs document.
        const content: string = await getGoogleDocsContent(
          fileId,
          oauthToken,
          "text/plain",
        );
        console.log("Content of the document:", content);
        // Trigger your Trigger.dev task with the metadata.
        taskResult = await callTriggerDevTask(content);
      } else {
        console.log("File is not a Google Docs file; ignoring.");
      }
    }

    // Return a JSON response indicating success.
    return new Response(
      JSON.stringify({ status: "meow", result: taskResult }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    );
  } catch (error) {
    console.error("Error triggering task:", error);
    return new Response(
      JSON.stringify({ status: "error", message: "Task invocation failed" }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});

/**
 * Refreshes the OAuth token using the stored refresh token.
 * This function uses the refresh token flow and expects necessary credentials to be set in the environment.
 *
 * @returns {Promise<string>} - A promise that resolves to the new access token.
 */
async function getAccessToken(): Promise<string> {
  const refreshToken: string | undefined = Deno.env.get("REFRESH_TOKEN");
  const clientId: string | undefined = Deno.env.get("CLIENT_ID");
  const clientSecret: string | undefined = Deno.env.get("CLIENT_SECRET");
  const redirectUri: string = Deno.env.get("REDIRECT_URI") ||
    "http://localhost";

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

  const response: Response = await fetch(
    "https://oauth2.googleapis.com/token",
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    },
  );

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to refresh access token: ${errorText}`);
  }

  const tokenData: OAuthTokenResponse = await response.json();
  return tokenData.access_token;
}

/**
 * Retrieves a list of changes from Google Drive starting from the provided saved start page token.
 *
 * @param {string} oauthToken - A valid OAuth access token.
 * @param {string} savedStartPageToken - The token from which to start listing changes (default is "74871").
 * @returns {Promise<DriveChange[]>} - A promise that resolves to an array of DriveChange objects.
 */
async function getChanges(
  oauthToken: string,
  savedStartPageToken: string = "74871",
): Promise<DriveChange[]> {
  // Build the URL for the changes.list endpoint.
  const url = new URL("https://www.googleapis.com/drive/v3/changes");
  url.searchParams.append("pageToken", savedStartPageToken);
  url.searchParams.append("fields", "*");

  // Make the request to the Drive API.
  const response: Response = await fetch(url.toString(), {
    headers: { "Authorization": `Bearer ${oauthToken}` },
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to fetch changes: ${errText}`);
  }

  // Parse the response as JSON.
  const data = await response.json() as ChangesResponse;

  if (data.changes && Array.isArray(data.changes)) {
    data.changes.forEach((change: DriveChange) => {
      console.log("Change found for file:", change.fileId);
    });
    return data.changes;
  } else {
    console.log("No changes found in this request.");
    return [];
  }
}

/**
 * Retrieves the exported content of a Google Docs file.
 *
 * @param fileId - The Google Docs file ID.
 * @param oauthToken - A valid OAuth access token with the required Drive scopes.
 * @param mimeType - (Optional) The MIME type in which to export the document. Defaults to plain text.
 * @returns {Promise<string>} - The content of the document in the specified format.
 */
async function getGoogleDocsContent(
  fileId: string,
  oauthToken: string,
  mimeType: string = "text/plain", // Change to "text/html", "application/pdf", etc., if needed
): Promise<string> {
  // Build the URL for exporting the file
  const url = new URL(
    `https://www.googleapis.com/drive/v3/files/${fileId}/export`,
  );
  url.searchParams.append("mimeType", mimeType);

  // Perform a GET request to the export endpoint with Authorization header
  const response = await fetch(url.toString(), {
    headers: { "Authorization": `Bearer ${oauthToken}` },
  });

  // If response not okay, throw an error with the details
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to export Google Docs content: ${errText}`);
  }

  // Retrieve the content as text
  return await response.text();
} /**
 * Retrieves the exported content of a Google Docs file.
 *
 * @param fileId - The Google Docs file ID.
 * @param oauthToken - A valid OAuth access token with the required Drive scopes.
 * @param mimeType - (Optional) The MIME type in which to export the document. Defaults to plain text.
 * @returns {Promise<string>} - The content of the document in the specified format.
 */

/**
 * Generates an OAuth token using service account credentials.
 * Expects the credentials JSON to be stored in the SERVICE_ACCOUNT_JSON environment variable.
 *
 * @returns {Promise<string>} - A promise that resolves to the access token.
 */
async function getOAuthToken(): Promise<string> {
  const svcAccountJson: string | undefined = Deno.env.get(
    "SERVICE_ACCOUNT_JSON",
  );
  if (!svcAccountJson) {
    throw new Error("SERVICE_ACCOUNT_JSON environment variable not set.");
  }
  const serviceAccount = JSON.parse(svcAccountJson);
  const privateKey: string = serviceAccount.private_key;
  const serviceAccountEmail: string = serviceAccount.client_email;

  // Define the JWT payload and header.
  const payload = {
    iss: serviceAccountEmail,
    scope: "https://www.googleapis.com/auth/drive",
    aud: "https://oauth2.googleapis.com/token",
    iat: getNumericDate(0),
    exp: getNumericDate(3600), // Token valid for 1 hour
  };
  const header = { alg: "RS256", typ: "JWT" };

  // Generate a signed JWT.
  const jwt: string = await create(header, payload, privateKey);

  // Prepare parameters for token exchange.
  const params = new URLSearchParams();
  params.append("grant_type", "urn:ietf:params:oauth:grant-type:jwt-bearer");
  params.append("assertion", jwt);

  const response: Response = await fetch(
    "https://oauth2.googleapis.com/token",
    {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(),
    },
  );

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to obtain OAuth token: ${errText}`);
  }

  const tokenData: OAuthTokenResponse = await response.json();
  return tokenData.access_token;
}

/**
 * Triggers a Trigger.dev task using file metadata.
 *
 * @param {DriveMetadata} fileMetadata - The metadata object returned by the Google Drive API.
 * @returns {Promise<void>} - A promise that resolves when the task is triggered.
 */
async function callTriggerDevTask(content: string): Promise<void> {
  // Trigger the openaiTask on Trigger.dev, passing a sample payload.
  const result = await tasks.trigger<typeof openaiTask>("openai-task", {
    prompt: content,
  });

  // Log the result from the Trigger.dev task.
  console.log("Trigger.dev task result:", result);
}
