export default function handler(req,res){ if(!req.headers.cookie) return res.status(401).end(); return res.json({id:req.query.id}); }
