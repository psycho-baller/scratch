// Import the built-in Supabase Edge Runtime type definitions for Deno
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import "jsr:@std/dotenv/load";

// Start the Deno edge function server. Supabase automatically calls this export.
Deno.serve(async (req: Request) => {
  try {
    // Allow only GET requests since this endpoint will be used as the OAuth callback.
    if (req.method !== "GET") {
      return new Response("Method Not Allowed", { status: 405 });
    }

    // Parse the URL and its query parameters from the incoming request.
    const url = new URL(req.url);
    // Extract the 'code' query parameter which contains the authorization code from Google.
    const code = url.searchParams.get("code");
    // Optionally, extract 'state' (if you used it for CSRF or session validation).
    const state = url.searchParams.get("state");

    // If there's no authorization code provided, return a 400 error.
    if (!code) {
      return new Response("Bad Request: Missing authorization code.", {
        status: 400,
      });
    }

    // Retrieve OAuth configuration values from the environment.
    const clientId = Deno.env.get("CLIENT_ID");
    const clientSecret = Deno.env.get("CLIENT_SECRET");
    const redirectUri = Deno.env.get("REDIRECT_URI");

    // Validate that all required OAuth configuration values are present.
    if (!clientId || !clientSecret || !redirectUri) {
      return new Response(
        "Internal Server Error: Missing OAuth configuration.",
        { status: 500 },
      );
    }

    // Build the URL-encoded request body for exchanging the authorization code.
    const params = new URLSearchParams();
    params.append("code", code); // The authorization code received from Google.
    params.append("client_id", clientId); // Your OAuth client ID.
    params.append("client_secret", clientSecret); // Your OAuth client secret.
    params.append("redirect_uri", redirectUri); // The redirect URI (should match this function's URL).
    params.append("grant_type", "authorization_code"); // The grant type is 'authorization_code'.

    // Make a POST request to Google's token endpoint to exchange the code for tokens.
    const tokenResponse = await fetch("https://oauth2.googleapis.com/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: params.toString(), // URL-encoded body data.
    });

    // If the token request failed, read the error message and return a 500 response.
    if (!tokenResponse.ok) {
      const errorText = await tokenResponse.text();
      return new Response(`Token request failed: ${errorText}`, {
        status: 500,
      });
    }

    // Parse the JSON response from Google. This contains the access_token, refresh_token, etc.
    const tokenData = await tokenResponse.json();

    // Optionally, here is where you might store the tokenData into a database or other storage.
    // For this example, we'll just include it in the response.

    // Return a 200 response with a JSON payload indicating success.
    return new Response(
      JSON.stringify({
        message: "Authorization successful! You can now close this window.",
        tokenData, // Contains access_token, refresh_token, token_type, etc.
        state, // You may use this to confirm if the state matches expectations.
      }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      },
    );
  } catch (error) {
    // Log any errors that occur during the process.
    console.error("Error processing OAuth callback:", error);
    // Return a 500 Internal Server Error response.
    return new Response(
      JSON.stringify({
        status: "error",
        message: "An error occurred during token exchange.",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
});
