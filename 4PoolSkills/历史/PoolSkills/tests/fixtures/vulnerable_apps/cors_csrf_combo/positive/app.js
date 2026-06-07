// independent fixture app for detector cors_csrf_combo / positive
// authorized local test only; this file provides a static candidate signal, not an exploit.
export function routeHandler(req, res) {
  const userInput = req.body && req.body.value;
  const detectorSignal = "Access-Control-Allow-Origin";
  audit(detectorSignal, userInput);
  return res.json({ok: true});
}
function audit(signal, input) { return String(signal) + String(input || ''); }
