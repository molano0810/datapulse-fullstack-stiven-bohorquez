import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { forkJoin, of, catchError } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { DashboardResumen, IndiceRiesgo } from '../../../core/models/api.models';



@Component({
  selector: 'app-dashboard-home',
  standalone: true,
  imports: [CommonModule, RouterModule, BaseChartDirective],
  templateUrl: './dashboard-home.component.html'
})
export class DashboardHomeComponent implements OnInit {
  private apiService = inject(ApiService);

  loading = signal(true);
  errorMsg = signal<string | null>(null);
  resumen = signal<DashboardResumen | null>(null);
  ranking = signal<IndiceRiesgo[]>([]);

  // Gráfica 1: Distribución de riesgo (Doughnut)
  doughnutData = signal<ChartData<'doughnut'>>({
    labels: ['Bajo', 'Moderado', 'Alto', 'Crítico'],
    datasets: [{
      data: [0, 0, 0, 0],
      backgroundColor: ['#198754', '#ffc107', '#fd7e14', '#dc3545']
    }]
  });

  doughnutOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'bottom' }
    }
  };

  // Gráfica 2: Ranking IRPC por País (Bar)
  barData = signal<ChartData<'bar'>>({
    labels: [],
    datasets: [{
      label: 'Índice IRPC (0 - 100)',
      data: [],
      backgroundColor: []
    }]
  });

  barOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true, max: 100 }
    },
    plugins: {
      legend: { display: false }
    }
  };

  ngOnInit(): void {
    this.cargarDatos();
  }

  cargarDatos(): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    forkJoin({
      resumen: this.apiService.getDashboardResumen(),
      ranking: this.apiService.getRankingRiesgo().pipe(catchError(() => of([])))
    }).subscribe({
      next: ({ resumen, ranking }) => {
        this.resumen.set(resumen);

        const listaRanking = Array.isArray(ranking) ? ranking : (ranking as any).results || [];
        this.ranking.set(listaRanking);

        // Actualizar Doughnut Chart
        const dist = resumen.distribucion_riesgo || { BAJO: 0, MODERADO: 0, ALTO: 0, CRITICO: 0 };
        this.doughnutData.set({
          labels: ['Bajo', 'Moderado', 'Alto', 'Crítico'],
          datasets: [{
            data: [dist.BAJO || 0, dist.MODERADO || 0, dist.ALTO || 0, dist.CRITICO || 0],
            backgroundColor: ['#198754', '#ffc107', '#fd7e14', '#dc3545'],
            borderWidth: 2
          }]
        });

        // Actualizar Bar Chart
        this.barData.set({
          labels: listaRanking.map((item: IndiceRiesgo) => item.pais_nombre),
          datasets: [{
            label: 'IRPC',
            data: listaRanking.map((item: IndiceRiesgo) => Number(item.indice_compuesto)),
            backgroundColor: listaRanking.map((item: IndiceRiesgo) => this.getColorPorNivel(item.nivel_riesgo)),
            borderRadius: 6
          }]
        });

        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set('No se pudieron cargar las métricas del dashboard. Verifica que el backend esté activo.');
        console.error(err);
      }
    });
  }

  getColorPorNivel(nivel: string): string {
    switch (nivel) {
      case 'BAJO': return '#198754';
      case 'MODERADO': return '#ffc107';
      case 'ALTO': return '#fd7e14';
      case 'CRITICO': return '#dc3545';
      default: return '#0d6efd';
    }
  }

  getBadgeClass(nivel: string): string {
    switch (nivel) {
      case 'BAJO': return 'bg-success';
      case 'MODERADO': return 'bg-warning text-dark';
      case 'ALTO': return 'bg-orange text-white';
      case 'CRITICO': return 'bg-danger';
      default: return 'bg-secondary';
    }
  }
}