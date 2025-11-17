import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';

import { AuthService } from '../auth/auth.service';
import { WeatherService, WeatherSummary } from '../services/weather.service';
import { ForecastHistoryResponse } from '../services/weather.service'; // si lo exportas

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  summary: WeatherSummary | null = null;
  loading = true;
  error: string | null = null;

  history: ForecastHistoryResponse | null = null;
  historyLoading = true;
  historyError: string | null = null;

  constructor(
    private authService: AuthService,
    private weatherService: WeatherService,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Resumen
    this.weatherService.getSummary().subscribe({
      next: (data) => {
        this.summary = data;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.error = 'Error al cargar el resumen de clima';
        this.loading = false;
      }
    });

    // Historial / detalle de pronósticos
    this.weatherService.getHistory().subscribe({
      next: (data) => {
        this.history = data;
        this.historyLoading = false;
      },
      error: (err) => {
        console.error(err);
        this.historyError = 'Error al cargar el historial de pronósticos';
        this.historyLoading = false;
      }
    });
  }

  logout() {
    this.authService.logout();
    this.router.navigate(['/auth/login']);
  }

  goToAlerts() {
    this.router.navigate(['/alerts']);
  }
}
