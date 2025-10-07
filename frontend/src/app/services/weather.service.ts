import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RainForecast {
  forecast_time: string;
  rain_mm: number;
  risk_level: number;
}

@Injectable({
  providedIn: 'root'
})
export class WeatherService {
  private apiUrl = 'http://localhost:5000/weather';

  constructor(private http: HttpClient) {}

  getForecasts(): Observable<RainForecast[]> {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
    return this.http.get<RainForecast[]>(`${this.apiUrl}/forecasts`, { headers });
  }
}
