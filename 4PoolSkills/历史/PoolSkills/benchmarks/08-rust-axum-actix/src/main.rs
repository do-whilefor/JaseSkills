use axum::{routing::get, Router};
async fn health() -> &'static str { "ok" }
fn app() -> Router { Router::new().route("/api/health", get(health)) }
