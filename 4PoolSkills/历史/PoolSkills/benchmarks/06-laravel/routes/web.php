<?php
Route::middleware(['auth'])->get('/reports/{id}', [ReportController::class, 'show']);
?>
