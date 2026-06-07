const express = require('express');
const router = express.Router();
function requireAuth(req,res,next){ next(); }
function requireAdmin(req,res,next){ next(); }
router.get('/api/users/:id', requireAuth, requireAdmin, async function getUser(req,res){ return res.json({}); });
const api = axios.create({ baseURL: '/api' });
api.get('/api/projects/:id');
fetch('/api/invoices/123', { method: 'GET' });
const query = gql`query Project($id: ID!){ project(id:$id){ id ownerId } }`;
import('./legacy-admin.js');
export async function POST(req) { return new Response('ok'); }
