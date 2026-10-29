import { useState } from "react";
import { Save, X } from "lucide-react";
import Button from "../ui/Button";
import Input from "../ui/Input";
import { TIPOS_VEHICULO } from "./constantes";

// Formulario de alta y edicion de un modelo del catalogo.
// Recibe modelo (null para crear), guardando, onGuardar(datos) y onCancelar.
export default function FormularioModelo({ modelo, guardando = false, onGuardar, onCancelar }) {
  const editando = Boolean(modelo);

  const [form, setForm] = useState(() => ({
    id: modelo?.id || "",
    marca: modelo?.marca || "",
    modelo: modelo?.modelo || "",
    tipo: modelo?.tipo || "furgoneta",
    largo_m: modelo?.largo_m ?? "",
    ancho_m: modelo?.ancho_m ?? "",
    alto_m: modelo?.alto_m ?? "",
    volumen_util_m3: modelo?.volumen_util_m3 ?? "",
    carga_util_kg: modelo?.carga_util_kg ?? "",
    fuente: modelo?.fuente || "",
    fuente_url: modelo?.fuente_url || "",
    verificado: Boolean(modelo?.verificado),
  }));
  const [errores, setErrores] = useState({});

  const cambiar = (campo) => (evento) => {
    const valor = evento.target.type === "checkbox" ? evento.target.checked : evento.target.value;
    setForm((actual) => ({ ...actual, [campo]: valor }));
    setErrores((actual) => ({ ...actual, [campo]: undefined }));
  };

  // Valida el formulario y devuelve el objeto de errores (vacio si todo esta bien).
  const validar = () => {
    const errs = {};
    if (!form.marca.trim()) errs.marca = "Indica la marca.";
    if (!form.modelo.trim()) errs.modelo = "Indica el modelo o linea.";
    if (form.id && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(form.id.trim())) {
      errs.id = "Usa minusculas, numeros y guiones (ej. toyota-hilux-2024).";
    }

    const largo = Number(form.largo_m);
    const ancho = Number(form.ancho_m);
    const alto = Number(form.alto_m);
    const volumen = Number(form.volumen_util_m3);
    const carga = Number(form.carga_util_kg);

    if (!(largo > 0 && largo < 20)) errs.largo_m = "Entre 0 y 20 metros.";
    if (!(ancho > 0 && ancho < 4)) errs.ancho_m = "Entre 0 y 4 metros.";
    if (!(alto > 0 && alto < 4)) errs.alto_m = "Entre 0 y 4 metros.";
    if (!(volumen > 0)) errs.volumen_util_m3 = "Debe ser mayor a 0.";
    if (!(carga > 0 && carga < 50000)) errs.carga_util_kg = "Entre 0 y 50 000 kg.";

    if (largo > 0 && ancho > 0 && alto > 0 && volumen > 0) {
      const teorico = largo * ancho * alto;
      if (volumen < teorico * 0.8 || volumen > teorico * 1.2) {
        errs.volumen_util_m3 = `Debe estar entre ${(teorico * 0.8).toFixed(2)} y ${(teorico * 1.2).toFixed(2)} m3 (dimensiones x +/-20%).`;
      }
    }

    if (form.fuente_url && !/^https?:\/\//i.test(form.fuente_url.trim())) {
      errs.fuente_url = "Debe empezar con http:// o https://.";
    }

    return errs;
  };

  const enviar = (evento) => {
    evento.preventDefault();
    const errs = validar();
    setErrores(errs);
    if (Object.values(errs).some(Boolean)) return;

    const datos = {
      marca: form.marca.trim(),
      modelo: form.modelo.trim(),
      tipo: form.tipo,
      largo_m: Number(form.largo_m),
      ancho_m: Number(form.ancho_m),
      alto_m: Number(form.alto_m),
      volumen_util_m3: Number(form.volumen_util_m3),
      carga_util_kg: Number(form.carga_util_kg),
      fuente: form.fuente.trim() || null,
      fuente_url: form.fuente_url.trim() || null,
      verificado: form.verificado,
    };
    if (!editando && form.id.trim()) datos.id = form.id.trim();
    onGuardar(datos);
  };

  return (
    <form onSubmit={enviar} noValidate className="space-y-4">
      <div>
        <h2 className="text-base font-bold text-slate-900">
          {editando ? "Editar modelo del catalogo" : "Agregar modelo al catalogo"}
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          {editando
            ? "Si el modelo viene del catalogo base, se guarda una copia propia sin tocar el JSON original."
            : "El modelo queda disponible para vincular placas y calcular capacidad."}
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="ID (opcional)"
          value={form.id}
          onChange={cambiar("id")}
          placeholder="toyota-hilux-2024"
          hint={editando ? "El ID no se modifica." : "Se genera desde marca y modelo si lo dejas vacio."}
          error={errores.id}
          disabled={editando}
        />
        <Input
          as="select"
          label="Tipo"
          value={form.tipo}
          onChange={cambiar("tipo")}
        >
          {TIPOS_VEHICULO.map((tipo) => (
            <option key={tipo.valor} value={tipo.valor}>
              {tipo.etiqueta}
            </option>
          ))}
        </Input>
        <Input label="Marca" value={form.marca} onChange={cambiar("marca")} placeholder="Toyota" error={errores.marca} />
        <Input label="Modelo / linea" value={form.modelo} onChange={cambiar("modelo")} placeholder="Hilux" error={errores.modelo} />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Input label="Largo (m)" type="number" min="0" step="0.01" value={form.largo_m} onChange={cambiar("largo_m")} error={errores.largo_m} />
        <Input label="Ancho (m)" type="number" min="0" step="0.01" value={form.ancho_m} onChange={cambiar("ancho_m")} error={errores.ancho_m} />
        <Input label="Alto (m)" type="number" min="0" step="0.01" value={form.alto_m} onChange={cambiar("alto_m")} error={errores.alto_m} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Volumen util (m3)"
          type="number"
          min="0"
          step="0.01"
          value={form.volumen_util_m3}
          onChange={cambiar("volumen_util_m3")}
          error={errores.volumen_util_m3}
          hint="Debe ser coherente con largo x ancho x alto (+/-20%)."
        />
        <Input
          label="Carga util (kg)"
          type="number"
          min="0"
          step="1"
          value={form.carga_util_kg}
          onChange={cambiar("carga_util_kg")}
          error={errores.carga_util_kg}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input label="Fuente" value={form.fuente} onChange={cambiar("fuente")} placeholder="Ficha tecnica oficial" />
        <Input
          label="URL de la fuente"
          value={form.fuente_url}
          onChange={cambiar("fuente_url")}
          placeholder="https://..."
          error={errores.fuente_url}
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={form.verificado}
          onChange={cambiar("verificado")}
          className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
        />
        Ficha verificada por el area de operaciones
      </label>

      <div className="flex gap-2 pt-2">
        <Button type="button" variant="secondary" block icon={X} onClick={onCancelar} disabled={guardando}>
          Cancelar
        </Button>
        <Button type="submit" block icon={Save} disabled={guardando}>
          {guardando ? "Guardando..." : editando ? "Guardar cambios" : "Agregar modelo"}
        </Button>
      </div>
    </form>
  );
}