@RestController
@RequestMapping("/api/admin")
class UserController {
  @GetMapping("/users")
  @PreAuthorize("hasRole('ADMIN')")
  public List<User> listUsers(@RequestParam String tenantId) { return List.of(); }
}
