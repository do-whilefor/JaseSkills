fn main(){ Router::new().route("/api/rust/users/:id", get(handler)); }
