import axios from 'axios';
const API_BASE = '/api';
export const client = axios.create({ baseURL: API_BASE, headers: { Authorization: 'Bearer redacted-example' }});
export function apiGet(path) { return client.get(path); }
export function apiPost(path, body) { return client.post(path, body); }
