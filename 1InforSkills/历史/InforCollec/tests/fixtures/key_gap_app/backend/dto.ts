class UpdateUserDto {
  userId: string;
  tenantId: string;
  role: string;
  debug?: boolean;
}
app.post('/api/admin/users', authMiddleware, updateUser);
function updateUser(req, res) { const x=req.body.tenantId; const y=req.query.include; }
const fillable = ['userId','tenantId','role','isAdmin'];
