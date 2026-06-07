// independent fixture app for detector graphql_authz / positive
// authorized local test only; this file provides a static candidate signal, not an exploit.
export function routeHandler(req, res) {
  const userInput = req.body && req.body.value;
  const detectorSignal = "GraphQL";
  audit(detectorSignal, userInput);
  return res.json({ok: true});
}
function audit(signal, input) { return String(signal) + String(input || ''); }
