import org.springframework.web.bind.annotation.*;
@RestController class UserController { @GetMapping("/api/users/{id}") public String get(@PathVariable String id){ return id; } }
