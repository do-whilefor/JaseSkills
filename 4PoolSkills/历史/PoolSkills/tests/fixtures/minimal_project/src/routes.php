<?php
Route::get('/api/v1/php/profile/{id}', 'ProfileController@show')->middleware('auth');
Route::post('/api/v1/php/upload', 'UploadController@store')->middleware('auth');
