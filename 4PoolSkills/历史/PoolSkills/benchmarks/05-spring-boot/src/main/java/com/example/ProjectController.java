package com.example;
import org.springframework.web.bind.annotation.*;
@RestController
@RequestMapping("/api")
class ProjectController {
  @GetMapping("/projects/{id}")
  public String project(@PathVariable String id) { return id; }
}
