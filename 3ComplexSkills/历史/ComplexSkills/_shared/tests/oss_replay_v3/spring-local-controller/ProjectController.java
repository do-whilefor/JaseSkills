@RestController @RequestMapping("/api") class ProjectController { @GetMapping("/projects/{id}") String get(){return "ok";} }
