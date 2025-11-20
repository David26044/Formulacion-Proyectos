import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterModule } from '@angular/router'; // 👈 agrega RouterModule acá
import { WeatherService, WeatherSummary } from '../services/weather.service';

@Component({
  selector: 'app-public-panel',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule           // 👈 y agrega RouterModule en imports
  ],
  templateUrl: './public-panel.component.html',
  styleUrls: ['./public-panel.component.css']
})
export class PublicPanelComponent implements OnInit {

  summary: WeatherSummary | null = null;
  loading = true;
  error: string | null = null;

  constructor(
    private weatherService: WeatherService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.weatherService.getSummary().subscribe({
      next: (data) => {
        this.summary = data;
        this.loading = false;
        console.log('Resumen público:', data);
      },
      error: (err) => {
        console.error(err);
        this.error = 'Error al cargar el estado hidráulico';
        this.loading = false;
      }
    });
  }

  goToRegister() {
    this.router.navigate(['/auth/register']);
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }
}
