$body = '{"email":"admin@clinic.com","password":"ChangeMe123!"}'
try {
    $r = Invoke-RestMethod -Uri 'http://localhost:8000/api/auth/login' -Method POST -ContentType 'application/json' -Body $body
    Write-Host "LOGIN SUCCESS - Role: $($r.role)"
    $token = $r.access_token
    $headers = @{ Authorization = "Bearer $token" }
    $doctors = Invoke-RestMethod -Uri 'http://localhost:8000/api/admin/doctors' -Headers $headers
    Write-Host "DOCTORS IN DB: $($doctors.Count)"
    $doctors | ForEach-Object { Write-Host " - Dr. $($_.full_name) | $($_.specialisation)" }
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Response: $($_.ErrorDetails.Message)"
}
