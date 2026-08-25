# NOVA Configuration Architecture

## Objetivo

El sistema de configuración centraliza la configuración de NOVA.

Los demás módulos no deben leer directamente archivos TOML.

## Flujo

Configuration File
        ↓
ConfigLoader
        ↓
ConfigManager
        ↓
ConfigurationService
        ↓
Core / UI / Services

## Responsabilidades

### ConfigLoader

Lee archivos TOML y crea los modelos de configuración.

### ConfigManager

Mantiene la configuración cargada y proporciona acceso centralizado.

### ConfigurationService

Expone la configuración al resto de NOVA mediante un servicio.

## Offline

La configuración debe funcionar sin Internet.

La conectividad real será responsabilidad de ConnectivityService.

## Secretos

Las credenciales y secretos nunca deben almacenarse en default.toml.

## Orbe

La configuración del Orbe se prepara en esta fase, pero su implementación pertenece a fases posteriores.

## Cambios

En esta primera implementación los cambios de configuración requieren reiniciar NOVA.