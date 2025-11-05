/** @odoo-module **/

import { registry } from '@web/core/registry';
import { ProgressBar } from '@web/core/progress_bar/progress_bar';
import { standardFieldProps } from "@web/views/fields/standard_field_props";

export class NineboxProgress extends ProgressBar {
    setup() {
        super.setup();
    }

    get options() {
        const options = super.options;
        options.colors = this.getProgressColors(this.props.value);
        return options;
    }

    getProgressColors(value) {
        if (value >= 100) return { success: true };
        if (value >= 75) return { info: true };
        if (value >= 50) return { warning: true };
        return { danger: true };
    }
}

NineboxProgress.template = 'web.ProgressBar';
NineboxProgress.props = {
    ...standardFieldProps,
    ...ProgressBar.props,
};

registry.category('fields').add('ninebox_progress', NineboxProgress);