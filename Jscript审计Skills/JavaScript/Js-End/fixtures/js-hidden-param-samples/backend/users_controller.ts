router.patch('/users/:id', requireAuth, async (req, res) => {
  const { email, role, isAdmin, tenantId, quota, status } = req.body;
  await userService.update(req.params.id, { email, role, isAdmin, tenantId, quota, status });
  res.json({ ok: true });
});
