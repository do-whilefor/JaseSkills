fn main() { Router::new().route("/api/v1/rust/users/:id", get(handler)); }
