import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { BaseChartDirective } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';
import { forkJoin, of, catchError } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { IndicadorEconomico, Pais, TipoCambio } from '../../../core/models/api.models';

@Component({
  selector: 'app-paises-list',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective],
  templateUrl: './paises-list.component.html'
})
export class PaisesListComponent implements OnInit {
  private apiService = inject(ApiService);

  paises = signal<Pais[]>([]);
  paisSeleccionado = signal<Pais | null>(null);
  indicadores = signal<IndicadorEconomico[]>([]);
  tiposCambio = signal<TipoCambio[]>([]);
  filtroTipo = signal<string>('');

  loadingPaises = signal(true);
  loadingDetalle = signal(false);
  errorMsg = signal<string | null>(null);

  tiposDisponibles = computed(() => {
    const tipos = this.indicadores().map(i => i.tipo);
    return Array.from(new Set(tipos));
  });

  indicadoresFiltrados = computed(() => {
    const filtro = this.filtroTipo();
    const lista = this.indicadores();
    return filtro ? lista.filter(i => i.tipo === filtro) : lista;
  });

  lineChartData = signal<ChartData<'line'>>({
    labels: [],
    datasets: []
  });

  lineChartOptions: ChartConfiguration<'line'>['options'] = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: true, position: 'top' }
    }
  };

  ngOnInit(): void {
    this.cargarPaises();
  }

  cargarPaises(): void {
    this.loadingPaises.set(true);
    this.errorMsg.set(null);

    this.apiService.getPaises().subscribe({
      next: (resp) => {
        const lista = Array.isArray(resp) ? resp : (resp as any).results || [];
        this.paises.set(lista);
        this.loadingPaises.set(false);

        if (lista.length > 0) {
          this.seleccionarPais(lista[0]);
        }
      },
      error: (err) => {
        this.loadingPaises.set(false);
        this.errorMsg.set('No se pudo cargar el catálogo de países.');
        console.error(err);
      }
    });
  }

  seleccionarPais(pais: Pais): void {
    this.paisSeleccionado.set(pais);
    this.loadingDetalle.set(true);
    this.filtroTipo.set('');

    forkJoin({
      indicadores: this.apiService.getPaisIndicadores(pais.id).pipe(catchError(() => of([]))),
      tiposCambio: this.apiService.getPaisTipoCambio(pais.id).pipe(catchError(() => of([])))
    }).subscribe({
      next: ({ indicadores, tiposCambio }) => {
        const listaInd = Array.isArray(indicadores) ? indicadores : (indicadores as any).results || [];
        const listaTc = Array.isArray(tiposCambio) ? tiposCambio : (tiposCambio as any).results || [];

        this.indicadores.set(listaInd);
        this.tiposCambio.set(listaTc);

        // Seleccionar por defecto el primer tipo de indicador para graficar
        const tipos = Array.from(new Set(listaInd.map((i: IndicadorEconomico) => i.tipo)));
        if (tipos.length > 0) {
          this.cambiarFiltroGrafica(tipos[0] as string);
        } else {
          this.lineChartData.set({ labels: [], datasets: [] });
        }

        this.loadingDetalle.set(false);
      },
      error: () => {
        this.loadingDetalle.set(false);
      }
    });
  }

  cambiarFiltroGrafica(tipo: string): void {
    this.filtroTipo.set(tipo);
    const serie = this.indicadores()
      .filter(i => !tipo || i.tipo === tipo)
      .sort((a, b) => a.anio - b.anio);

    if (!tipo && this.tiposDisponibles().length > 0) {
      this.actualizarGrafica(this.tiposDisponibles()[0]);
    } else {
      this.actualizarGrafica(tipo);
    }
  }

  private actualizarGrafica(tipo: string): void {
    const serie = this.indicadores()
      .filter(i => i.tipo === tipo)
      .sort((a, b) => a.anio - b.anio);

    const unidad = serie[0]?.unidad || '';
    this.lineChartData.set({
      labels: serie.map(s => s.anio.toString()),
      datasets: [
        {
          label: `${tipo} (${unidad})`,
          data: serie.map(s => Number(s.valor)),
          borderColor: '#0d6efd',
          backgroundColor: 'rgba(13, 110, 253, 0.15)',
          fill: true,
          tension: 0.3,
          pointRadius: 4
        }
      ]
    });
  }
}