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

  // --- Países ---
    getPaises(): Observable<Pais[]> {
        return this.http.get<Pais[]>(`${this.baseUrl}/paises/`);
    }

    getPaisDetalle(id: number): Observable<Pais> {
        return this.http.get<Pais>(`${this.baseUrl}/paises/${id}/`);
    }

  // --- Motor IRPC (Riesgo País) ---
    getRankingRiesgo(): Observable<IndiceRiesgo[]> {
        return this.http.get<IndiceRiesgo[]>(`${this.baseUrl}/riesgo/`);
    }

    recalcularRiesgo(paisId?: number): Observable<any> {
        const body = paisId ? { pais_id: paisId } : {};
        return this.http.post<any>(`${this.baseUrl}/riesgo/calcular/`, body);
    }

  // --- Portafolios ---
    getPortafolios(): Observable<Portafolio[]> {
        return this.http.get<Portafolio[]>(`${this.baseUrl}/portafolios/`);
    }

  // --- Alertas ---
    getAlertas(): Observable<Alerta[]> {
        return this.http.get<Alerta[]>(`${this.baseUrl}/alertas/`);
    }

  // --- Logs de Auditoría ---
    getLogs(): Observable<any[]> {
        return this.http.get<any[]>(`${this.baseUrl}/logs/`);
    }
}