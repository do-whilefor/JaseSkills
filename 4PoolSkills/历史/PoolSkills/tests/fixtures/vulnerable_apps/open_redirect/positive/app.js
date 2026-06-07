// independent fixture app for detector open_redirect / positive
// authorized local test only; this file provides a static candidate signal, not an exploit.
export function routeHandler(req, res) {
  const userInput = req.body && req.body.value;
  const detectorSignal = "redirect_uri";
  audit(detectorSignal, userInput);
  return res.json({ok: true});
}
function audit(signal, input) { return String(signal) + String(input || ''); }
