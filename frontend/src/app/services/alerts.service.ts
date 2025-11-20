import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AlertConfig {
  email: string;
  notify_on_high: boolean;
  notify_on_very_high: boolean;
}

@Injectable({
  providedIn: 'root'
})
export class AlertsService {
  private apiUrl = 'https://formulacion-proyectos.onrender.com/alerts';

  constructor(private http: HttpClient) {}

  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('token') || '';
    return new HttpHeaders({
      Authorization: `Bearer ${token}`
    });
  }

  getConfig(): Observable<AlertConfig> {
    const headers = this.getAuthHeaders();
    return this.http.get<AlertConfig>(`${this.apiUrl}/config`, { headers });
  }

  updateConfig(config: AlertConfig): Observable<AlertConfig> {
    const headers = this.getAuthHeaders();
    return this.http.put<AlertConfig>(`${this.apiUrl}/config`, config, { headers });
  }
}
