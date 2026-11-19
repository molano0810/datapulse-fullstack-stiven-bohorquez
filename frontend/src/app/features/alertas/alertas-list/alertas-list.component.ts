import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../../core/services/api.service';
import { Alerta } from '../../../core/models/api.models';

@Component({
  selector: 'app-alertas-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './alertas-list.component.html'
})
export class AlertasListComponent implements OnInit {
  private apiService = inject(ApiService);

  alertas = signal<Alerta[]>([]);
  filtroEstado = signal<'TODAS' | 'NO_LEIDAS' | 'LEIDAS'>('TODAS');
  filtroSeveridad = signal<string>('TODAS');

  loading = signal(true);
  procesando = signal(false);
  errorMsg = signal<string | null>(null);

  noLeidasCount = computed(() => this.alertas().filter(a => !a.leida).length);
  criticasCount = computed(() => this.alertas().filter(a => a.severidad === 'CRITICAL' && !a.leida).length);
  advertenciasCount = computed(() => this.alertas().filter(a => a.severidad === 'WARNING' && !a.leida).length);

  alertasFiltradas = computed(() => {
    const estado = this.filtroEstado();
    const sev = this.filtroSeveridad();

    return this.alertas().filter(a => {
      const cumpleEstado =
        estado === 'TODAS' ||
        (estado === 'NO_LEIDAS' && !a.leida) ||
        (estado === 'LEIDAS' && a.leida);

      const cumpleSev = sev === 'TODAS' || a.severidad === sev;
      return cumpleEstado && cumpleSev;
    });
  });

  ngOnInit(): void {
    this.cargarAlertas();
  }

  cargarAlertas(): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    this.apiService.getAlertas().subscribe({
      next: (resp) => {
        const lista = Array.isArray(resp) ? resp : (resp as any).results || [];
        this.alertas.set(lista);
        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set('No se pudieron cargar las alertas del sistema.');
        console.error(err);
      }
    });
  }

  marcarLeida(alerta: Alerta): void {
    if (alerta.leida) return;

    this.apiService.marcarAlertaLeida(alerta.id).subscribe({
      next: () => {
        this.alertas.update(lista =>
          lista.map(item => (item.id === alerta.id ? { ...item, leida: true } : item))
        );
      },
      error: () => {
        this.errorMsg.set('No se pudo actualizar el estado de la alerta.');
      }
    });
  }

  marcarTodasLeidas(): void {
    if (this.noLeidasCount() === 0) return;

    this.procesando.set(true);
    this.apiService.marcarTodasAlertasLeidas().subscribe({
      next: () => {
        this.alertas.update(lista => lista.map(item => ({ ...item, leida: true })));
        this.procesando.set(false);
      },
      error: () => {
        this.procesando.set(false);
        this.errorMsg.set('No se pudieron marcar todas las alertas como leídas.');
      }
    });
  }

  getSeveridadBadge(severidad: string): string {
    switch (severidad) {
      case 'CRITICAL': return 'bg-danger';
      case 'WARNING': return 'bg-warning text-dark';
      case 'INFO': return 'bg-info text-dark';
      default: return 'bg-secondary';
    }
  }
}