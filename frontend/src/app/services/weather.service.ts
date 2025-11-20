import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface WeatherSummary {
  current_rain: {
    intensity_mm_h: number;
    label: string;
  };
  current_risk: {
    level: string;   // "BAJO" | "MODERADO" | "ALTO" | "MUY ALTO"
    score: number;
    color: string;   // "green" | "yellow" | "orange" | "red"
    message: string;
    // debug puede quedar o no en la interfaz, si lo quieres usar:
    debug?: {
      I_now_mm_h: number;
      P_24h_mm: number;
      P_48h_mm: number;
      peso_I: number;
      peso_P24: number;
      peso_P48: number;
    };
  };
  next_hours: {
    window_hours: number;   // debería ser 6
    accumulated_mm: number; // lluvia total 6 horas
    level: string;          // "Seco" | "Moderado" | "Fuerte"
    bars: number;           // 1, 2 o 3
  };
}


export interface RainForecast {
  forecast_time: string;
  rain_mm: number;
  risk_level: number;
}

export interface ForecastHistoryEntry {
  time: string;
  rain_3h_mm: number;
  intensity_mm_h: number;
  slot_risk: string;
}

export interface ForecastHistorySummary {
  max_intensity_mm_h: number;
  max_intensity_time: string | null;
  total_24h_mm: number;
  total_48h_mm: number;
}

export interface ForecastHistoryResponse {
  entries: ForecastHistoryEntry[];
  summary: ForecastHistorySummary;
}

@Injectable({
  providedIn: 'root'
})
export class WeatherService {
  private apiUrl = 'https://formulacion-proyectos.onrender.com/weather';

  constructor(private http: HttpClient) {}

  getForecasts(): Observable<RainForecast[]> {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
    return this.http.get<RainForecast[]>(`${this.apiUrl}/forecasts`, { headers });
  }

    getSummary(): Observable<WeatherSummary> {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
    return this.http.get<WeatherSummary>(`${this.apiUrl}/summary`, { headers });
  }
  getHistory(): Observable<ForecastHistoryResponse> {
    const token = localStorage.getItem('token');
    const headers = new HttpHeaders({
    Authorization: `Bearer ${token}`
    });
    return this.http.get<ForecastHistoryResponse>(`${this.apiUrl}/history`, { headers });
}

}
