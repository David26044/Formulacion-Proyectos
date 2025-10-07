import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { NgForm, FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css'],
  standalone: true,
  imports: [CommonModule, FormsModule],
})
export class RegisterComponent {
  errorMessage: string | null = null;
  successMessage: string | null = null;

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit(form: NgForm) {
    if (form.valid) {
      const { name, email, password } = form.value;
      this.authService.register(name, email, password).subscribe({
        next: () => {
          this.successMessage = 'Registro exitoso, ya puedes iniciar sesión';
          setTimeout(() => this.router.navigate(['/auth/login']), 1500);
        },
        error: (err) => {
          this.errorMessage = err.error?.message || 'Error en el registro';
        },
      });
    }
  }

  goToLogin() {
    this.router.navigate(['/auth/login']);
  }
}
