$content = Get-Content "ventas.py" -Raw -Encoding UTF8

# Reemplazar el contenido problemático
$newContent = $content -replace [regex]::Escape('            if modo_pago == "� Pago mixto":
                st.markdown("**Selecciona múltiples tipos de pago:**")
                col_pago1, col_pago2 = st.columns(2)
                
                with col_pago1:
                    pago_efectivo = st.checkbox("💵 Efectivo", value=True, key="efectivo_final")
                    pago_tarjeta = st.checkbox("💳 Tarjeta", key="tarjeta_final")
                
                with col_pago2:
                    pago_transferencia = st.checkbox("📱 Transferencia", key="transferencia_final")
                    pago_credito = st.checkbox("📋 Crédito", key="credito_final")
                
            else:
                # Configurar pagos únicos basados en la selección
                pago_efectivo = modo_pago == "💵 Efectivo"
                pago_tarjeta = modo_pago == "💳 Tarjeta"
                pago_transferencia = modo_pago == "📱 Transferencia"
                pago_credito = modo_pago == "📋 Crédito"'), '            if modo_pago == "💵 Pago único":
                tipo_pago_unico = st.radio(
                    "Selecciona el tipo de pago:",
                    ["💵 Efectivo", "💳 Tarjeta", "📱 Transferencia", "📋 Crédito"],
                    index=0,
                    horizontal=False,
                    key="tipo_pago_unico_final"
                )
                
                pago_efectivo = tipo_pago_unico == "💵 Efectivo"
                pago_tarjeta = tipo_pago_unico == "💳 Tarjeta"
                pago_transferencia = tipo_pago_unico == "📱 Transferencia"
                pago_credito = tipo_pago_unico == "📋 Crédito"
                
            else:
                st.markdown("**Selecciona múltiples tipos de pago:**")
                col_pago1, col_pago2 = st.columns(2)
                
                with col_pago1:
                    pago_efectivo = st.checkbox("💵 Efectivo", value=True, key="efectivo_final")
                    pago_tarjeta = st.checkbox("💳 Tarjeta", key="tarjeta_final")
                
                with col_pago2:
                    pago_transferencia = st.checkbox("📱 Transferencia", key="transferencia_final")
                    pago_credito = st.checkbox("📋 Crédito", key="credito_final")'

# Guardar el archivo
$newContent | Set-Content "ventas.py" -Encoding UTF8