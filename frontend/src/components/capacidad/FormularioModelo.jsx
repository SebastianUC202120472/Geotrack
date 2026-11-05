
import { useState } from "react";
import { Save, X } from "lucide-react";

import Button from "../ui/Button";
import Input from "../ui/Input";
import { TIPOS_VEHICULO } from "./constantes";

// ============================================================
// FORMULARIO DEL CATALOGO DE VEHICULOS - IDEA 3
// Permite registrar y editar modelos del catalogo.
// Valida dimensiones, volumen, carga y fuentes tecnicas.
// ============================================================

export default function FormularioModelo({
  modelo,
  guardando = false,
  onGuardar,
  onCancelar,
}) {
  const editando = Boolean(modelo);

  // ============================================================
  // ESTADO INICIAL DEL FORMULARIO
  // ============================================================

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

  // ============================================================
  // ACTUALIZAR CAMPOS
  // ============================================================

  const cambiar = (campo) => (evento) => {
    const valor =
      evento.target.type === "checkbox"
        ? evento.target.checked
        : evento.target.value;

    setForm((actual) => {
      const siguiente = {
        ...actual,
        [campo]: valor,
      };

      // Cuando cambian datos tecnicos de una ficha ya
      // verificada, se requiere una nueva comprobacion.
      const camposTecnicos = [
        "marca",
        "modelo",
        "tipo",
        "largo_m",
        "ancho_m",
        "alto_m",
        "volumen_util_m3",
        "carga_util_kg",
        "fuente",
        "fuente_url",
      ];

      if (camposTecnicos.includes(campo)) {
        siguiente.verificado = false;
      }

      return siguiente;
    });

    setErrores((actual) => ({
      ...actual,
      [campo]: undefined,
    }));
  };

  // ============================================================
  // VALIDACIONES DEL FORMULARIO
  // ============================================================

  const validar = () => {
    const errs = {};

    // Validar identificador.
    if (
      form.id &&
      !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(form.id.trim())
    ) {
      errs.id =
        "Utiliza letras minusculas, numeros y guiones.";
    }

    // Validar marca.
    if (!form.marca.trim()) {
      errs.marca = "La marca es obligatoria.";
    } else if (form.marca.trim().length > 60) {
      errs.marca = "La marca no debe superar 60 caracteres.";
    }

    // Validar modelo.
    if (!form.modelo.trim()) {
      errs.modelo = "El modelo es obligatorio.";
    } else if (form.modelo.trim().length > 80) {
      errs.modelo = "El modelo no debe superar 80 caracteres.";
    }

    // Validar tipo.
    if (
      !TIPOS_VEHICULO.some(
        (tipo) => tipo.valor === form.tipo,
      )
    ) {
      errs.tipo = "Selecciona un tipo de vehiculo valido.";
    }

    // Convertir medidas a numeros.
    const largo = Number(form.largo_m);
    const ancho = Number(form.ancho_m);
    const alto = Number(form.alto_m);
    const volumen = Number(form.volumen_util_m3);
    const carga = Number(form.carga_util_kg);

    // Validar largo.
    if (
      form.largo_m === "" ||
      !Number.isFinite(largo) ||
      largo <= 0 ||
      largo >= 20
    ) {
      errs.largo_m =
        "El largo debe ser mayor a 0 y menor a 20 metros.";
    }

    // Validar ancho.
    if (
      form.ancho_m === "" ||
      !Number.isFinite(ancho) ||
      ancho <= 0 ||
      ancho >= 4
    ) {
      errs.ancho_m =
        "El ancho debe ser mayor a 0 y menor a 4 metros.";
    }

    // Validar alto.
    if (
      form.alto_m === "" ||
      !Number.isFinite(alto) ||
      alto <= 0 ||
      alto >= 4
    ) {
      errs.alto_m =
        "El alto debe ser mayor a 0 y menor a 4 metros.";
    }

    // Validar volumen util.
    if (
      form.volumen_util_m3 === "" ||
      !Number.isFinite(volumen) ||
      volumen <= 0 ||
      volumen >= 200
    ) {
      errs.volumen_util_m3 =
        "El volumen debe ser mayor a 0 y menor a 200 m3.";
    }

    // Validar carga util.
    if (
      form.carga_util_kg === "" ||
      !Number.isFinite(carga) ||
      carga <= 0 ||
      carga >= 50000
    ) {
      errs.carga_util_kg =
        "La carga debe ser mayor a 0 y menor a 50000 kg.";
    }

    // ========================================================
    // COMPROBAR COHERENCIA DE LAS DIMENSIONES
    // ========================================================

    if (
      largo > 0 &&
      ancho > 0 &&
      alto > 0 &&
      volumen > 0 &&
      Number.isFinite(largo) &&
      Number.isFinite(ancho) &&
      Number.isFinite(alto) &&
      Number.isFinite(volumen)
    ) {
      const volumenTeorico = largo * ancho * alto;

      const minimo = volumenTeorico * 0.80;
      const maximo = volumenTeorico * 1.20;

      if (
        volumen < minimo ||
        volumen > maximo
      ) {
        errs.volumen_util_m3 =
          `El volumen debe estar entre ` +
          `${minimo.toFixed(2)} y ` +
          `${maximo.toFixed(2)} m3, ` +
          `segun las dimensiones registradas.`;
      }
    }

    // ========================================================
    // VALIDAR FUENTE TECNICA
    // ========================================================

    if (!form.fuente.trim()) {
      errs.fuente =
        "Debes indicar una ficha tecnica de referencia.";
    } else if (form.fuente.trim().length > 200) {
      errs.fuente =
        "La fuente no debe superar 200 caracteres.";
    }

    if (!form.fuente_url.trim()) {
      errs.fuente_url =
        "Debes ingresar la URL de la ficha tecnica.";
    } else if (form.fuente_url.trim().length > 300) {
      errs.fuente_url =
        "La URL no debe superar 300 caracteres.";
    } else {
      try {
        const url = new URL(
          form.fuente_url.trim(),
        );

        if (url.protocol !== "https:") {
          errs.fuente_url =
            "La ficha tecnica debe utilizar HTTPS.";
        } else if (
          url.username ||
          url.password ||
          !url.hostname
        ) {
          errs.fuente_url =
            "La URL no debe contener credenciales.";
        } else if (
          url.hostname === "localhost" ||
          url.hostname === "127.0.0.1" ||
          url.hostname.endsWith(".local")
        ) {
          errs.fuente_url =
            "Debes utilizar una fuente publica.";
        }
      } catch {
        errs.fuente_url =
          "La URL ingresada no es valida.";
      }
    }

    return errs;
  };

  // ============================================================
  // ENVIAR DATOS AL COMPONENTE PRINCIPAL
  // ============================================================

  const enviar = (evento) => {
    evento.preventDefault();

    if (guardando) {
      return;
    }

    const errs = validar();

    setErrores(errs);

    if (Object.values(errs).some(Boolean)) {
      return;
    }

    const datos = {
      marca: form.marca.trim(),
      modelo: form.modelo.trim(),
      tipo: form.tipo,

      largo_m: Number(form.largo_m),
      ancho_m: Number(form.ancho_m),
      alto_m: Number(form.alto_m),

      volumen_util_m3: Number(
        form.volumen_util_m3,
      ),

      carga_util_kg: Number(
        form.carga_util_kg,
      ),

      fuente: form.fuente.trim(),
      fuente_url: form.fuente_url.trim(),

      verificado: form.verificado,
    };

    // El ID solamente puede indicarse al crear.
    if (
      !editando &&
      form.id.trim()
    ) {
      datos.id = form.id.trim();
    }

    onGuardar(datos);
  };

  // ============================================================
  // INTERFAZ DEL FORMULARIO
  // ============================================================

  return (
    <form
      onSubmit={enviar}
      noValidate
      className="space-y-4"
    >
      {/* ENCABEZADO */}
      <div>
        <h2 className="text-base font-bold text-slate-900">
          {editando
            ? "Editar modelo del catalogo"
            : "Agregar modelo al catalogo"}
        </h2>

        <p className="mt-1 text-xs text-slate-500">
          {editando
            ? "Los cambios se guardan en el modulo sin modificar el JSON original."
            : "Registra un vehiculo para utilizarlo en la calculadora y vincularlo a la flota."}
        </p>
      </div>

      {/* IDENTIFICACION DEL VEHICULO */}
      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="ID del modelo (opcional)"
          value={form.id}
          onChange={cambiar("id")}
          placeholder="toyota-hilux-2024"
          hint={
            editando
              ? "El ID del modelo no se modifica."
              : "Se genera automaticamente si lo dejas vacio."
          }
          error={errores.id}
          disabled={editando}
        />

        <Input
          as="select"
          label="Tipo de vehiculo"
          value={form.tipo}
          onChange={cambiar("tipo")}
          error={errores.tipo}
        >
          {TIPOS_VEHICULO.map((tipo) => (
            <option
              key={tipo.valor}
              value={tipo.valor}
            >
              {tipo.etiqueta}
            </option>
          ))}
        </Input>

        <Input
          label="Marca"
          value={form.marca}
          onChange={cambiar("marca")}
          placeholder="Toyota"
          error={errores.marca}
        />

        <Input
          label="Modelo"
          value={form.modelo}
          onChange={cambiar("modelo")}
          placeholder="Hilux"
          error={errores.modelo}
        />
      </div>

      {/* MEDIDAS INTERNAS */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-slate-800">
          Dimensiones internas de carga
        </h3>

        <div className="grid gap-4 sm:grid-cols-3">
          <Input
            label="Largo (m)"
            type="number"
            min="0.01"
            max="19.99"
            step="0.01"
            value={form.largo_m}
            onChange={cambiar("largo_m")}
            error={errores.largo_m}
          />

          <Input
            label="Ancho (m)"
            type="number"
            min="0.01"
            max="3.99"
            step="0.01"
            value={form.ancho_m}
            onChange={cambiar("ancho_m")}
            error={errores.ancho_m}
          />

          <Input
            label="Alto (m)"
            type="number"
            min="0.01"
            max="3.99"
            step="0.01"
            value={form.alto_m}
            onChange={cambiar("alto_m")}
            error={errores.alto_m}
          />
        </div>
      </div>

      {/* CAPACIDAD DEL VEHICULO */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-slate-800">
          Capacidad de carga
        </h3>

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Volumen util (m3)"
            type="number"
            min="0.001"
            max="199.99"
            step="0.001"
            value={form.volumen_util_m3}
            onChange={cambiar("volumen_util_m3")}
            error={errores.volumen_util_m3}
            hint="El volumen debe ser coherente con las dimensiones internas."
          />

          <Input
            label="Carga util (kg)"
            type="number"
            min="0.01"
            max="49999"
            step="0.01"
            value={form.carga_util_kg}
            onChange={cambiar("carga_util_kg")}
            error={errores.carga_util_kg}
          />
        </div>
      </div>

      {/* FUENTES TECNICAS */}
      <div>
        <h3 className="mb-3 text-sm font-semibold text-slate-800">
          Fuente de informacion tecnica
        </h3>

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Fuente"
            value={form.fuente}
            onChange={cambiar("fuente")}
            placeholder="Ficha tecnica oficial del fabricante"
            error={errores.fuente}
          />

          <Input
            label="URL de la fuente"
            value={form.fuente_url}
            onChange={cambiar("fuente_url")}
            placeholder="https://fabricante.com/ficha-tecnica"
            error={errores.fuente_url}
          />
        </div>

        <p className="mt-2 text-xs text-slate-500">
          Utiliza una ficha tecnica que respalde las
          dimensiones internas y la carga util indicada.
        </p>
      </div>

      {/* VERIFICACION */}
      <div className="rounded-lg border border-slate-200 p-3">
        <label className="flex items-start gap-3 text-sm text-slate-700">
          <input
            type="checkbox"
            checked={form.verificado}
            onChange={cambiar("verificado")}
            className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-500"
          />

          <span>
            <strong>
              Ficha tecnica verificada
            </strong>

            <span className="mt-1 block text-xs text-slate-500">
              Marca esta opcion solamente despues
              de comprobar que las medidas y la carga
              util coinciden con la documentacion tecnica.
            </span>
          </span>
        </label>
      </div>

      {/* BOTONES */}
      <div className="flex gap-2 pt-2">
        <Button
          type="button"
          variant="secondary"
          block
          icon={X}
          onClick={onCancelar}
          disabled={guardando}
        >
          Cancelar
        </Button>

        <Button
          type="submit"
          block
          icon={Save}
          disabled={guardando}
        >
          {guardando
            ? "Guardando..."
            : editando
              ? "Guardar cambios"
              : "Agregar modelo"}
        </Button>
      </div>
    </form>
  );
}
