/** @odoo-module **/


import { SelectionField } from "@web/views/fields/selection/selection_field";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";


export class CustomSelectionField extends SelectionField {
    get string() {
        if (this.type === "char") {
            
            const value = this.props.record.data[this.props.name];
            const option = this.options.find((o) => o[0] === value);
            return option ? option[1] : '';
        } else {
            return super.string(); 
        }
    }
    onChange(ev) {
        if (this.type === "char") {

        
            const newValue = ev.target.value.slice(1, -1);
            this.props.record.update({ [this.props.name]: newValue }, { save: this.props.autosave });
           
            
        } else {
            super.onChange(ev);
        }
    }
    get options() {
        if (Boolean(this.props.record.data.possible_values.match(/^\[\s*\['[^']*'\s*,\s*'[^']*'\]\s*(?:,\s*\['[^']*'\s*,\s*'[^']*'\]\s*)*\]$/))) {
            return  eval(this.props.record.data.possible_values);
        } else {
            return eval([[]]);
        }
    }
}

export const customSelectionField = {
    component: CustomSelectionField,
    displayName: _t("Custom Selection"),
    supportedTypes: ["char"],
};

registry.category("fields").add("custom_selection", customSelectionField);