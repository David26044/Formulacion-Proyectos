// src/app/alerts/alerts-settings.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AlertsService, AlertConfig } from '../services/alerts.service';

@Component({
  selector: 'app-alerts-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alerts-settings.component.html',
  styleUrls: ['./alerts-settings.component.css']
})
export class AlertsSettingsComponent implements OnInit {
  config: AlertConfig = {
    email: '',
    notify_on_high: true,
    notify_on_very_high: true
  };

  loading = true;
  saving = false;
  message: string | null = null;
  error: string | null = null;

  constructor(private alertsService: AlertsService) {}

  ngOnInit(): void {
    this.alertsService.getConfig().subscribe({
      next: (cfg) => {
        this.config = cfg;
        this.loading = false;
      },
      error: (err) => {
        console.error(err);
        this.error = 'Error al cargar la configuración de alertas';
        this.loading = false;
      }
    });
  }

  save() {
    this.saving = true;
    this.message = null;
    this.error = null;

    this.alertsService.updateConfig(this.config).subscribe({
      next: (cfg) => {
        this.config = cfg;
        this.saving = false;
        this.message = 'Configuración guardada correctamente';
      },
      error: (err) => {
        console.error(err);
        this.error = 'Error al guardar la configuración';
        this.saving = false;
      }
    });
  }
}
