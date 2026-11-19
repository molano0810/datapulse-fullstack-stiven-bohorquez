import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { forkJoin } from 'rxjs';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { Pais, Portafolio } from '../../../core/models/api.models';

@Component({
  selector: 'app-portafolios-list',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './portafolios-list.component.html'
})
export class PortafoliosListComponent implements OnInit {
  private apiService = inject(ApiService);
  public authService = inject(AuthService);

  portafolios = signal<Portafolio[]>([]);
  paises = signal<Pais[]>([]);
  seleccionado = signal<Portafolio | null>(null);

  loading = signal(true);
  guardando = signal(false);
  simulando = signal(false);
  exportando = signal(false);

  mensajeExito = signal<string | null>(null);
  errorMsg = signal<string | null>(null);

  // Formulario nuevo portafolio
  mostrarFormPortafolio = signal(false);
  nuevoPortafolio = {
    nombre: '',
    descripcion: '',
    es_publico: false
  };

  // Formulario nueva posición
  mostrarFormPosicion = signal(false);
  nuevaPosicion = {
    pais: '',
    tipo_activo: 'RENTA_VARIABLE',
    monto_inversion_usd: 50000,
    fecha_entrada: new Date().toISOString().slice(0, 10),
    notas: ''
  };

  tiposActivo = [
    { valor: 'RENTA_FIJA', etiqueta: 'Renta Fija' },
    { valor: 'RENTA_VARIABLE', etiqueta: 'Renta Variable' },
    { valor: 'COMMODITIES', etiqueta: 'Commodities' },
    { valor: 'MONEDA', etiqueta: 'Moneda' }
  ];

  // Parámetros y resultado del simulador
  simParams = {
    variacion_cambiaria_pct: -5.0,
    horizonte_meses: 12
  };
  resultadoSimulacion = signal<any | null>(null);

  capitalPortafolioSeleccionado = computed(() => {
    const p = this.seleccionado();
    if (!p?.posiciones) return 0;
    return p.posiciones.reduce((acc, item) => acc + Number(item.monto_inversion_usd || 0), 0);
  });

  ngOnInit(): void {
    this.cargarDatosIniciales();
  }

  cargarDatosIniciales(mantenerId?: number): void {
    this.loading.set(true);
    this.errorMsg.set(null);

    forkJoin({
      portafolios: this.apiService.getPortafolios(),
      paises: this.apiService.getPaises()
    }).subscribe({
      next: ({ portafolios, paises }) => {
        const listaPort = Array.isArray(portafolios) ? portafolios : (portafolios as any).results || [];
        const listaPaises = Array.isArray(paises) ? paises : (paises as any).results || [];

        this.portafolios.set(listaPort);
        this.paises.set(listaPaises);

        if (listaPaises.length > 0 && !this.nuevaPosicion.pais) {
          this.nuevaPosicion.pais = listaPaises[0].codigo_iso;
        }

        if (listaPort.length > 0) {
          const objetivo = mantenerId
            ? listaPort.find((item: Portafolio) => item.id === mantenerId) || listaPort[0]
            : listaPort[0];
          this.seleccionarPortafolio(objetivo);
        } else {
          this.seleccionado.set(null);
        }

        this.loading.set(false);
      },
      error: (err) => {
        this.loading.set(false);
        this.errorMsg.set('No se pudieron cargar los portafolios de inversión.');
        console.error(err);
      }
    });
  }

  seleccionarPortafolio(portafolio: Portafolio): void {
    this.seleccionado.set(portafolio);
    this.resultadoSimulacion.set(null);
    this.mostrarFormPosicion.set(false);
  }

  crearPortafolio(): void {
    if (!this.nuevoPortafolio.nombre.trim()) return;

    this.guardando.set(true);
    this.errorMsg.set(null);
    this.mensajeExito.set(null);

    this.apiService.crearPortafolio(this.nuevoPortafolio).subscribe({
      next: (creado) => {
        this.guardando.set(false);
        this.mostrarFormPortafolio.set(false);
        this.nuevoPortafolio = { nombre: '', descripcion: '', es_publico: false };
        this.mensajeExito.set(`Portafolio "${creado.nombre}" creado correctamente.`);
        this.cargarDatosIniciales(creado.id);
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorMsg.set(
          err.status === 403
            ? 'Tu rol (VIEWER) no tiene permisos para crear portafolios.'
            : 'No se pudo crear el portafolio.'
        );
      }
    });
  }

  agregarPosicion(): void {
    const port = this.seleccionado();
    if (!port || !this.nuevaPosicion.pais || this.nuevaPosicion.monto_inversion_usd <= 0) return;

    this.guardando.set(true);
    this.errorMsg.set(null);
    this.mensajeExito.set(null);

    this.apiService.agregarPosicion(port.id, this.nuevaPosicion).subscribe({
      next: () => {
        this.guardando.set(false);
        this.mostrarFormPosicion.set(false);
        this.nuevaPosicion.notas = '';
        this.mensajeExito.set('Posición de inversión registrada en el portafolio.');
        this.cargarDatosIniciales(port.id);
      },
      error: (err) => {
        this.guardando.set(false);
        this.errorMsg.set(
          err.status === 403
            ? 'Tu rol (VIEWER) no tiene permisos para modificar posiciones.'
            : 'Error al registrar la posición. Verifica los campos.'
        );
      }
    });
  }

  ejecutarSimulacion(): void {
    const port = this.seleccionado();
    if (!port) return;

    this.simulando.set(true);
    this.errorMsg.set(null);

    this.apiService.simularPortafolio(port.id, this.simParams).subscribe({
      next: (resp) => {
        const detalle = resp.detalle_posiciones || [];
        const totalInvertido =
          resp.total_invertido_usd ??
          resp.total_invertido ??
          detalle.reduce((acc: number, d: any) => acc + Number(d.monto_actual_usd || 0), 0);
        const valorProyectado =
          resp.valor_proyectado_usd ??
          resp.valor_proyectado ??
          detalle.reduce((acc: number, d: any) => acc + Number(d.monto_proyectado_usd || 0), 0);
        const irpcPonderado =
          resp.irpc_ponderado ??
          (totalInvertido > 0
            ? detalle.reduce((acc: number, d: any) => acc + Number(d.monto_actual_usd || 0) * Number(d.irpc_pais || 0), 0) / totalInvertido
            : 0);

        this.resultadoSimulacion.set({
          totalInvertido,
          valorProyectado,
          variacionTotal: valorProyectado - totalInvertido,
          irpcPonderado,
          detalle
        });
        this.simulando.set(false);
      },
      error: () => {
        this.simulando.set(false);
        this.errorMsg.set('No se pudo ejecutar la simulación del portafolio.');
      }
    });
  }

  descargarCsv(): void {
    const port = this.seleccionado();
    if (!port) return;

    this.exportando.set(true);
    this.apiService.exportarPortafolioCsv(port.id).subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `portafolio_${port.id}_${port.nombre.toLowerCase().replace(/\s+/g, '_')}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
        this.exportando.set(false);
      },
      error: () => {
        this.exportando.set(false);
        this.errorMsg.set('No se pudo exportar el archivo CSV.');
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