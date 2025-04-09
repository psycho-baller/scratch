const jwt = require("jsonwebtoken");

// Your Supabase JWT secret—replace this with your actual secret from Supabase dashboard
const supabaseJwtSecret = "x3oq2DIQsFUhy/mvpZ9JQA0m8KWklpiGvmCZ/giMMU9Q0e7aSZjba9Cn16NUkDKvJmZNEO596TIJ0M0IPVf5og==";

// Define your payload.
// The 'sub' field is typically the user's ID, and 'exp' is the expiration time.
// You can also include additional claims if needed.
const payload = {
  sub: "13f45d21-cbc2-4603-9142-b5b519df2b68", // The subject (typically a user ID)
  // Set expiration to 1 hour (3600 seconds) from now
  exp: Math.floor(Date.now() / 1000) + 3600,
  // You can also add other custom claims here, for instance:
  // role: "authenticated"
};

// Sign the token using HS256 algorithm.
const token = jwt.sign(payload, supabaseJwtSecret, { algorithm: "HS256" });

console.log("Generated JWT token:", token);