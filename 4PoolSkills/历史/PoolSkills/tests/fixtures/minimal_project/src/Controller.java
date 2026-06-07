@RestController
class Controller {
  @GetMapping("/api/v1/java/accounts/{id}")
  public String account(){ return "ok"; }
}
