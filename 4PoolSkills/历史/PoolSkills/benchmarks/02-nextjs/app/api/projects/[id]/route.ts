export async function GET(req: Request, ctx: { params: { id: string } }) { return Response.json({ id: ctx.params.id }); }
