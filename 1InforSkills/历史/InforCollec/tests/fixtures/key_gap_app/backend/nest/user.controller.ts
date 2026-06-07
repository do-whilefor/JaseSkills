@Controller('api/internal')
export class InternalController {
  @Get('feature-flags')
  @UseGuards(JwtAuthGuard, RolesGuard)
  listFlags() { return []; }
}
