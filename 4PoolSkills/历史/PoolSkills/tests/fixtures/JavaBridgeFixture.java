import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api")
class JavaBridgeFixture {
  @GetMapping("/projects/{id}")
  public String getProject(@PathVariable String id) { return "ok"; }
  @PostMapping(path="/admin/users")
  public String createUser(@RequestBody String body) { return "ok"; }
}
