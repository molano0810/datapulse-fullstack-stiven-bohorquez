import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
    Alerta,
    DashboardResumen,
    IndicadorEconomico,
    IndiceRiesgo,
    Pais,
    Portafolio,
    TipoCambio
} from '../models/api.models';

@Injectable({
    providedIn: 'root'
})
export class ApiService {
    private http = inject(HttpClient);
    private baseUrl = environment.apiUrl;

  // --- Dashboard ---
    getDashboardResumen(): Observable<DashboardResumen> {
        return this.http.get<DashboardResumen>(`${this.baseUrl}/dashboard/resumen/`);
    }

  // --- Países e Indicadores ---
    getPaises(): Observable<Pais[]> {
        return this.http.get<Pais[]>(`${this.baseUrl}/paises/`);
    }

    getPaisDetalle(id: number): Observable<Pais> {
        return this.http.get<Pais>(`${this.baseUrl}/paises/${id}/`);
    }

    getPaisIndicadores(paisId: number, tipo?: string): Observable<IndicadorEconomico[]> {
        let params = new HttpParams();
        if (tipo) params = params.set('tipo', tipo);
        return this.http.get<IndicadorEconomico[]>(`${this.baseUrl}/paises/${paisId}/indicadores/`, { params });
    }

    getPaisTipoCambio(paisId: number): Observable<TipoCambio[]> {
        return this.http.get<TipoCambio[]>(`${this.baseUrl}/paises/${paisId}/tipo-cambio/`);
    }

  // --- Motor IRPC (Riesgo País) ---
    getRankingRiesgo(): Observable<IndiceRiesgo[]> {
        return this.http.get<IndiceRiesgo[]>(`${this.baseUrl}/riesgo/`);
    }

    getRiesgoHistorico(id: number): Observable<IndiceRiesgo[]> {
        return this.http.get<IndiceRiesgo[]>(`${this.baseUrl}/riesgo/${id}/historico/`);
    }

    recalcularRiesgo(paisId?: number): Observable<any> {
        const body = paisId ? { pais_id: paisId } : {};
        return this.http.post<any>(`${this.baseUrl}/riesgo/calcular/`, body);
    }

  // --- Portafolios ---
    getPortafolios(): Observable<Portafolio[]> {
        return this.http.get<Portafolio[]>(`${this.baseUrl}/portafolios/`);
    }

    getPortafolioDetalle(id: number): Observable<Portafolio> {
        return this.http.get<Portafolio>(`${this.baseUrl}/portafolios/${id}/`);
    }

    crearPortafolio(payload: Partial<Portafolio>): Observable<Portafolio> {
        return this.http.post<Portafolio>(`${this.baseUrl}/portafolios/`, payload);
    }

    agregarPosicion(portafolioId: number, payload: any): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/portafolios/${portafolioId}/posiciones/`, payload);
    }

    simularPortafolio(portafolioId: number, payload: any): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/portafolios/${portafolioId}/simular/`, payload);
    }

    exportarPortafolioCsv(portafolioId: number): Observable<Blob> {
        return this.http.get(`${this.baseUrl}/portafolios/${portafolioId}/exportar/`, {
            responseType: 'blob'
        });
    }

  // --- Alertas ---
    getAlertas(): Observable<Alerta[]> {
        return this.http.get<Alerta[]>(`${this.baseUrl}/alertas/`);
    }

    getAlertasResumen(): Observable<any> {
        return this.http.get<any>(`${this.baseUrl}/alertas/resumen/`);
    }

    marcarAlertaLeida(id: number): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/alertas/${id}/leer/`, {});
    }

    marcarTodasAlertasLeidas(): Observable<any> {
        return this.http.post<any>(`${this.baseUrl}/alertas/leer-todas/`, {});
    }

  // --- Auditoría ---
    getLogs(): Observable<any[]> {
        return this.http.get<any[]>(`${this.baseUrl}/logs/`);
    }
}