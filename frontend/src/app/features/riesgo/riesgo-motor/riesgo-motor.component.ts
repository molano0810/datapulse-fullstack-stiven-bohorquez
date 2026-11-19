import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { ApiService } from '../../../core/services/api.service';
import { IndiceRiesgo } from '../../../core/models/api.models';

@Component({
  selector: 'app-riesgo-motor',
  standalone: true,
  imports: [CommonModule, BaseChartDirective],
  templateUrl: './riesgo-motor.component.html'
})
export class RiesgoMotorComponent implements OnInit {
  private apiService = inject(ApiService);

  ranking = signal<IndiceRiesgo[]>([]);
  seleccionado = signal<IndiceRiesgo | null>(null);
  historico = signal<IndiceRiesgo[]>([]);

  loading = signal(true);
  calculando = signal(false);
  mensajeExito = signal<string | null>(null);
  errorMsg = signal<string | null>(null);

  historicoChartData = signal<ChartData<'line'>>({
    labels: [],
    datasets: []
  });

  historicoChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true, max: 100 }
    }
  };

  ngOnInit(): void {
    this.cargarRanking();
  }

  cargarRanking(): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    this.apiService.getRankingRiesgo().subscribe({
      next: (resp) => {
        const lista = Array.isArray(resp) ? resp : (resp as any).results || [];
        this.ranking.set(lista);
        this.loading.set(false);

        if (lista.length > 0) {
          this.verDetalle(lista[0]);
        }
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set('No se pudo obtener la matriz del Motor IRPC.');
        console.error(err);
      }
    });
  }

  recalcular(paisId?: string): void {
    this.calculando.set(true);
    this.mensajeExito.set(null);
    this.errorMsg.set(null);

    this.apiService.recalcularRiesgo(paisId).subscribe({
      next: (resp) => {
        this.calculando.set(false);
        this.mensajeExito.set(
          resp?.mensaje || (paisId ? 'Índice IRPC del país recalculado.' : 'Motor IRPC regional recalculado exitosamente.')
        );
        this.cargarRanking();
      },
      error: (err) => {
        this.calculando.set(false);
        if (err.status === 403) {
          this.errorMsg.set('Tu rol actual (VIEWER) no tiene permisos para ejecutar el recálculo del Motor IRPC.');
        } else {
          this.errorMsg.set('Ocurrió un error al recalcular el índice IRPC.');
        }
      }
    });
  }

  verDetalle(item: IndiceRiesgo): void {
    this.seleccionado.set(item);

    this.apiService.getRiesgoHistorico(item.pais).subscribe({
      next: (resp) => {
        const lista = Array.isArray(resp) ? resp : (resp as any).results || [];
        this.historico.set(lista);

        const ordenado = [...lista].reverse();
        this.historicoChartData.set({
          labels: ordenado.map(h => new Date(h.fecha_calculo).toLocaleDateString()),
          datasets: [
            {
              label: `Evolución IRPC - ${item.pais_nombre}`,
              data: ordenado.map(h => Number(h.indice_compuesto)),
              borderColor: '#0d6efd',
              backgroundColor: 'rgba(13, 110, 253, 0.1)',
              fill: true,
              tension: 0.25
            }
          ]
        });
      },
      error: () => {
        this.historico.set([]);
      }
    });
  }

  getBadgeClass(nivel: string): string {
    switch (nivel) {
      case 'BAJO': return 'bg-success';
      case 'MODERADO': return 'bg-warning text-dark';
      case 'ALTO': return 'bg-danger';
      case 'CRITICO': return 'bg-dark';
      default: return 'bg-secondary';
    }
  }
}