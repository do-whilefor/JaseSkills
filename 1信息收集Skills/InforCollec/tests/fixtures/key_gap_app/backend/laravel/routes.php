<?php
Route::post('/api/payments/callback', [PaymentController::class, 'callback'])->middleware('auth:webhook');
